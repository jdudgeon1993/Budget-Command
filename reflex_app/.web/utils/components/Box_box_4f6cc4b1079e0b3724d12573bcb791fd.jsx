
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_4f6cc4b1079e0b3724d12573bcb791fd = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_34c21647b3fcc3206525c129f8ee09a0 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.do_copy_allocs", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#6868a2", ["cursor"] : "pointer", ["padding"] : "5px 10px", ["borderRadius"] : "6px", ["border"] : "1px solid #252535", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["&:hover"] : ({ ["color"] : "#8282a2", ["borderColor"] : "#3c3c56" }) }),onClick:on_click_34c21647b3fcc3206525c129f8ee09a0},children)
    )
});
