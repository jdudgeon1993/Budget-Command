
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_52afea37e262fb8763248a20607b2155 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_8956e1e0622b3ffcc11ed47b06886255 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.delete_from_edit_tx", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "1", ["padding"] : "10px", ["borderRadius"] : "8px", ["border"] : "1px solid #FF453A44", ["color"] : "#FF453A", ["fontSize"] : "12px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["letterSpacing"] : "0.06em", ["&:hover"] : ({ ["background"] : "#FF453A11" }) }),onClick:on_click_8956e1e0622b3ffcc11ed47b06886255},children)
    )
});
