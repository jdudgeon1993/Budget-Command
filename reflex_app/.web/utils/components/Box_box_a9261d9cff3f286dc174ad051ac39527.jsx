
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_a9261d9cff3f286dc174ad051ac39527 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_70f1e87e283c9ca1c1d5ac88c9d5049d = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.vault_release_pool", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "8px 12px", ["borderRadius"] : "8px", ["border"] : "1px solid #f8717144", ["color"] : "#f87171", ["fontSize"] : "12px", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["&:hover"] : ({ ["background"] : "#f8717111" }) }),onClick:on_click_70f1e87e283c9ca1c1d5ac88c9d5049d},children)
    )
});
